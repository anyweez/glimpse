import collections, numpy

from decorators import genreq


Biome = collections.namedtuple('Biome', ['name', 't', 'm'])

# based on Whittaker biome mapping method:
# https://en.wikipedia.org/wiki/Biome#/media/File:Climate_influence_on_terrestrial_biome.svg
#
# viz of this biome map:
# https://docs.google.com/spreadsheets/d/1rVZWZPXZbnGT94hQLeA7CLGXkBN1Ut27s36EwJizIWI/edit#gid=0
biomes = [
    Biome('Tundra', t=(0.0, 0.2), m=(0.0, 0.4)),            # cold and dry. do not go here.
    Biome('Boreal forest', t=(0.0, 0.3), m=(0.4, 1.0)),
    Biome('Temperate grassland', t=(0.2, 0.6), m=(0.0, 0.3)),
    Biome('Temperate forest', t=(0.2, 0.8), m=(0.3, 0.4)),
    Biome('Temperate forest', t=(0.3, 0.8), m=(0.4, 1.0)),
    Biome('Desert', t=(0.6, 1.0), m=(0.0, 0.3)),
    Biome('Desert', t=(0.8, 1.0), m=(0.3, 0.4)),
    Biome('Rainforest', t=(0.8, 1.0), m=(0.4, 1.0)),
]

def GetBiome(biome_id=None, name=None):
    if biome_id:
        return biomes[biome_id]
    
    if name:
        return [b for b in biomes if b.name == name][0]

@genreq(cellprops=['temperature', 'moisture'])
def generate(world, vd):

    def identify_biome(idx):
        '''
        A cell's biome is defined by its average temperature and moisture. Each temperature/moisture combination
        corresponds to exactly one biome type.
        '''
        for biome_id, biome in enumerate(biomes):
            if world.cp_temperature[idx] >= biome.t[0] and world.cp_temperature[idx] <= biome.t[1]:
                if world.cp_moisture[idx] >= biome.m[0] and world.cp_moisture[idx] <= biome.m[1]:
                    return biome_id

        raise Exception('Not a member of any biome @ t=%f, m=%f; must be an internal error with biome configurations.' % (world.cp_temperature[idx], world.cp_moisture[idx]))

    biome_list = [identify_biome(idx) for idx in world.cell_idxs()]
    biome_arr = world.new_cp_array(numpy.uint8, biome_list)

    world.add_cell_property('biome', biome_arr)