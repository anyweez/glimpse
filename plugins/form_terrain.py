import random, numpy, collections

from noise import snoise2

from world import Cell
from decorators import genreq

# seed = random.randint(0, 1000)

# def __gen_noise(x, y, config):
#     scaled_x = x / config['scale']
#     scaled_y = y / config['scale']

#     octaves = config['octaves']
#     persistence = config['persistence']
#     lacunarity = config['lacunarity']

#     base = config['base']

#     return ( snoise2(scaled_x, scaled_y, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=base) + 1.0) / 2.0

def randfloat(low, high):
    diff = high - low
    return (random.random() * diff) + low

# def cap(val, low, high):
#     if val < low:
#         return low
#     if val > high:
#         return high
    
#     return val

# def pe_converge(self_elev, target_elev, dist):
#     goal_elev = max(self_elev, target_elev) + 0.1
#     return goal_elev / dist

# def pe_diverge(self_elev, target_elev, dist):
#     goal_elev = min(self_elev, target_elev) - 0.1
#     return goal_elev / dist

# def pe_transform(self_elev, target_elev, dist):
#     return 0.0

#########
NoiseWeight = collections.namedtuple('NoiseWeight', ['weight', 'scale', 'octaves'])
noise_weights = [
    NoiseWeight(weight=0.8, scale=3, octaves=4),
    NoiseWeight(weight=0.2, scale=4, octaves=8),
    NoiseWeight(weight=0.1, scale=8, octaves=16)
]

shift_weight = NoiseWeight(weight=0.6, scale=None, octaves=None)
noise_base = random.randint(0, 1000)

def calc_shift(x, y):
	x_dist = min(x, 1.0 - x)
	y_dist = min(y, 1.0 - y)

	smaller = min(x_dist, y_dist)

	if smaller < 0.15:
		return (0.15 - smaller) / 0.15
	
	return 0.0

def noise_xy(x, y):
    all_weights = sum( [nw.weight for nw in noise_weights] )

    total = 0.0
    for nw in noise_weights:
        weight = nw.weight / all_weights

        # Shift noise from [-1, 1] to [0, 1]
        base = 0.5 * (snoise2(x * nw.scale, y * nw.scale, nw.octaves, base=noise_base) + 1.0)

        total += (weight * base)

    return total

@genreq(cellprops=['latitude', 'longitude', 'plate'])
def generate(world, vd):
    elevation_list = []

    for idx in world.cell_idxs():
        longitude = world.cp_longitude[idx]
        latitude = world.cp_latitude[idx]

        base = noise_xy(longitude, latitude)
        shift = calc_shift(longitude, latitude) * shift_weight.weight

        elevation_list.append( max(0.01, min(0.99, base - shift)) )

    elevation_arr = world.new_cp_array(numpy.double, elevation_list)
    world.add_cell_property('elevation', elevation_arr)

    WaterlineHeight = randfloat(0.35, 0.6)

    def celltype(elevation):
        return Cell.Type.LAND if elevation > WaterlineHeight else Cell.Type.WATER

    celltype_list = [celltype(world.cp_elevation[idx]) for idx in world.cell_idxs()]
    celltype_arr = world.new_cp_array(None, celltype_list)

    world.add_cell_property('celltype', celltype_arr)
    world.set_param('WaterlineHeight', WaterlineHeight)

    depth_list = []
    for idx in world.cell_idxs():
        if world.cp_celltype[idx] == Cell.Type.WATER:
            depth_list.append( WaterlineHeight - world.cp_elevation[idx] )
        else:
            depth_list.append(0.0)
    
    depth_arr = world.new_cp_array(numpy.double, depth_list)
    world.add_cell_property('depth', depth_arr)


# @genreq(cellprops=['latitude', 'longitude', 'plate'])
# def generate(world, vd):
#     '''
#     This plugin has two functions:

#     1) Add elevation to all cells
#     2) Mark all cells as either 'land' or 'water'
#     '''

#     # Definition of what these are here:
#     # http://libnoise.sourceforge.net/glossary/
#     NoiseConfig = {
#         'scale': 3.0,           # top tweak
#         'octaves': 6,
#         'persistence': 1.35,    # amplitude multiplier
#         'lacunarity': 1.5,      # frequency multiplier
#         'base': random.randint(0, 1000)
#     }

#     WaterlineHeight = randfloat(0.3, 0.65)

#     world.set_param('WaterlineHeight', WaterlineHeight)

#     ##
#     ## Calculate elevation. Contributions from plate tectonics and simplex noise.
#     ##
#     noise_contrib = 0.7 #0.6
#     plate_contrib = 0.1 #0.2
#     plate_effect_contrib = 0.2 #0.2

#     def init_elev(idx):
#         # return layered_noise(world.cp_latitude[idx], world.cp_longitude[idx])
#         return __gen_noise(world.cp_latitude[idx], world.cp_longitude[idx], NoiseConfig)

#     elev_noise = [init_elev(idx) for idx in world.cell_idxs()]

#     # Adjust height of cells based on the plate they're a part of
#     num_plates = max(world.cp_plate) + 1
#     plate_height = [randfloat(-1, 1) for _ in range(num_plates)]

#     # Apply effects at plate boundary
#     plate_effects = (pe_converge, pe_diverge)
#     boundaries = {}
#     for first_idx in range(num_plates):
#         for second_idx in range(num_plates):
#             func = random.choice(plate_effects)

#             boundaries[(first_idx, second_idx)] = func
#             boundaries[(second_idx, first_idx)] = func

#     elev_plate_eff = [0.0,] * len(world.cell_idxs()) # modifications due to plate effects

#     # Find plate boundaries and calculate elevation adjustments
#     for cell_idx in world.cell_idxs():
#         (target_idx, dist) = world.graph.distance(cell_idx, lambda idx: world.cp_plate[idx] != world.cp_plate[cell_idx])

#         # TODO: convert '4' to std_density -- plate_effects need to accomodate arbitrary distances
#         if dist is not None and dist <= 15:
#             plate_key = (world.cp_plate[cell_idx], world.cp_plate[target_idx])
#             cell_elev = elev_noise[cell_idx]
#             target_elev = elev_noise[target_idx]

#             elev_plate_eff[cell_idx] = boundaries[plate_key](cell_elev, target_elev, dist)

#     # apply plate effect modifications to the elevation list array
#     elevation_list = [ 
#         (elev_noise[idx] * noise_contrib) + (plate_height[world.cp_plate[idx]] * plate_contrib) + (elev_plate_eff[idx] * plate_effect_contrib)
#         for idx in world.cell_idxs()
#     ]

#     # elevation_arr = world.new_cp_array(numpy.double, normalize(elevation_list))
#     elevation_arr = world.new_cp_array(numpy.double, [ cap(e, 0.0, 0.99) for e in elevation_list ])

#     ##
#     ## Apply celltype based on elevation.
#     ##

#     def celltype(elevation):
#         return Cell.Type.LAND if elevation > WaterlineHeight else Cell.Type.WATER

#     # Determine which cells are land vs water
#     celltype_arr = world.new_cp_array(
#         None, 
#         [ celltype(elevation_arr[idx]) for idx in world.cell_idxs() ],
#     )

#     world.add_cell_property('elevation', elevation_arr)
#     world.add_cell_property('celltype', celltype_arr)