import random, numpy, collections

from noise import snoise2

from world import Cell
from decorators import genreq

def randfloat(low, high):
    diff = high - low
    return (random.random() * diff) + low

#########
NoiseWeight = collections.namedtuple('NoiseWeight', ['weight', 'scale', 'octaves'])
noise_weights = [
    NoiseWeight(weight=0.8, scale=3, octaves=4),
    NoiseWeight(weight=0.2, scale=4, octaves=8),
    NoiseWeight(weight=0.1, scale=8, octaves=16)
]

shift_weight = NoiseWeight(weight=0.6, scale=None, octaves=None)
noise_base = random.randint(0, 1000)

def noise_xyz(x, y):
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

    # Calculate height based on lat/long. This is currently wrapping around the
    # antimeridian but is not wrapping around the poles.
    for idx in world.cell_idxs():
        latitude, longitude = vd.centroid(idx)
        base = noise_xyz((latitude + 90) / 180, (longitude + 180) / 360)

        elevation_list.append( max(0.01, min(0.99, base)) )

    elevation_arr = world.new_cp_array(numpy.double, elevation_list)
    world.add_cell_property('elevation', elevation_arr)

    WaterlineHeight = randfloat(0.45, 0.75)

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