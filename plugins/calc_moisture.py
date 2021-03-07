import random, numpy, collections

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

NoiseWeight = collections.namedtuple('NoiseWeight', ['weight', 'scale', 'octaves'])
noise_weights = [
    NoiseWeight(weight=0.8, scale=2, octaves=4),
    NoiseWeight(weight=0.2, scale=4, octaves=8),
    NoiseWeight(weight=0.1, scale=8, octaves=16)
]
noise_base = random.randint(0, 1000)

def noise_xy(x, y):
    all_weights = sum( [nw.weight for nw in noise_weights] )

    total = 0.0
    for nw in noise_weights:
        weight = nw.weight / all_weights

        # Shift noise from [-1, 1] to [0, 1]
        base = 0.5 * (snoise2(x * nw.scale, y * nw.scale, nw.octaves, base=noise_base) + 1.0)

        total += (weight * base)

    return total

@genreq(cellprops=['celltype', 'latitude', 'longitude'], worldparams=['has_lakes'])
def generate(world, vd):

    def calculate_cell_moisture(idx):
        latitude, longitude = vd.centroid(idx)

        base = noise_xy(
            (latitude + 90) / 180, 
            (longitude + 180) / 360,
        )

        (_, dist_water) = world.graph.distance(idx, lambda dest_idx: world.cp_celltype[dest_idx] == Cell.Type.WATER)

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