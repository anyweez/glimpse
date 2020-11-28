import random, numpy

from noise import snoise2

from world import Cell
from decorators import genreq

def __gen_noise(x, y, config):
    scaled_x = x / config['scale']
    scaled_y = y / config['scale']

    octaves = config['octaves']
    persistence = config['persistence']
    lacunarity = config['lacunarity']

    base = config['base']

    return ( snoise2(scaled_x, scaled_y, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=base) + 1.0) / 2.0

def randfloat(low, high):
    diff = high - low
    return (random.random() * diff) + low

def cap(val, low, high):
    if val < low:
        return low
    if val > high:
        return high
    
    return val


@genreq(cellprops=['latitude', 'longitude', 'plate'])
def generate(world, vd):
    '''
    This plugin has two functions:

    1) Add elevation to all cells
    2) Mark all cells as either 'land' or 'water'
    '''

    # Definition of what these are here:
    # http://libnoise.sourceforge.net/glossary/
    NoiseConfig = {
        'scale': 4.5,           # top tweak
        'octaves': 5,
        'persistence': 4.5,
        'lacunarity': 2.0,
        'base': random.randint(0, 1000)
    }

    WaterlineHeight = randfloat(0.2, 0.55)

    world.set_param('WaterlineHeight', WaterlineHeight)

    # Calculate elevation. Contributions from plate tectonics and simplex noise.
    noise_contrib = 0.70
    plate_contrib = 0.30

    def init_elev(idx):
        return __gen_noise(world.cp_latitude[idx], world.cp_longitude[idx], NoiseConfig)

    elevation_list = [init_elev(idx) * noise_contrib for idx in world.cell_idxs()]

    # Adjust height of cells based on the plate they're a part of
    num_plates = max(world.cp_plate) + 1
    plate_height = [randfloat(plate_contrib * -1, plate_contrib) for _ in range(num_plates)]

    def shift_by_plate(idx, elevation):
        return cap(plate_height[world.cp_plate[idx]] + elevation, 0.0, 1.0)

    elevation_list = [ shift_by_plate(idx, elev) for idx, elev in enumerate(elevation_list) ]
    elevation_arr = world.new_cp_array(numpy.double, elevation_list)

    def celltype(elevation):
        return Cell.Type.LAND if elevation > WaterlineHeight else Cell.Type.WATER

    # Determine which cells are land vs water
    celltype_arr = world.new_cp_array(
        None, 
        [ celltype(elevation_list[idx]) for idx in world.cell_idxs() ],
    )

    world.add_cell_property('elevation', elevation_arr)
    world.add_cell_property('celltype', celltype_arr)