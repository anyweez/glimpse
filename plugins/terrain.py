import random, numpy

from noise import snoise2

from structs import Cell

def __gen_noise(x, y, config):
    scaled_x = x / config['scale']
    scaled_y = y / config['scale']

    octaves = config['octaves']
    persistence = config['persistence']
    lacunarity = config['lacunarity']

    base = config['base']

    return ( snoise2(scaled_x, scaled_y, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=base) + 1.0) / 2.0


def generate(world, vd):
    '''
    This plugin has two functions:

    1) Add elevation to all cells
    2) Mark all cells as either 'land' or 'water'
    '''

    NoiseConfig = {
        'scale': 4.5,           # top tweak
        'octaves': 5,
        'persistence': 4.5,
        'lacunarity': 2.0,
        'base': random.randint(0, 1000)
    }

    WaterlineHeight = (random.random() / 4.0) + 0.4 # range = [0.4, 0.65)

    world.set_param('WaterlineHeight', WaterlineHeight)

    # Calculate elevation using simplex noise
    elevation_arr = world.new_cp_array(numpy.double, default_value=0)

    for idx in world.cell_idxs():
        elevation_arr[idx] = __gen_noise(world.cp_latitude[idx], world.cp_longitude[idx], NoiseConfig)

    def celltype(elevation):
        return Cell.Type.LAND if elevation > WaterlineHeight else Cell.Type.WATER

    # Determine which cells are land vs water
    celltype_arr = world.new_cp_array(
        None, 
        [ celltype(elevation_arr[idx]) for idx in world.cell_idxs() ],
    )

    world.add_cell_property('elevation', elevation_arr)
    world.add_cell_property('celltype', celltype_arr)