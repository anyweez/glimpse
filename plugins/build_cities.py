import random, numpy, math

from entity import Entity
from world import Cell
from decorators import genreq
from cultures.human import HumanCulture

class City(Entity):
    def __init__(self, cell_idx):
        super().__init__(None)
        self.cell_idx = cell_idx

    def render_stage2(self, ctx, world, vd, theme):
        city_radius = 0.01
        city_loc = Entity._transform_pt((
            world.cp_latitude[self.cell_idx],
            world.cp_longitude[self.cell_idx],
        ))

        ctx.set_source_rgba(*theme.CityFill)
        ctx.arc(city_loc[0], city_loc[1], city_radius, 0, 2 * math.pi)
        ctx.fill_preserve()

        ctx.set_source_rgba(*theme.CityBorder)
        ctx.set_line_width(0.004)

        ctx.stroke()

@genreq(cellprops=['elevation', 'celltype'])
def generate(world, vd):
    SampleSize = 25
    # TODO: make city count dynamic
    CityCount = random.randint(5, 18)

    cultures = [
        HumanCulture(None, world), # Target: HumanCulture(lang)
    ]
    cities = []

    def score(region_idx, culture):
        '''
        Calculate the score of an individual cell for the specified culture. Higher scores
        are more desirable.
        '''
        existing_cells = set( map(lambda city: city.cell_idx, cities) )

        return culture.city_survivability(region_idx, existing_cells) + \
            culture.city_economy(region_idx, existing_cells) - \
            culture.city_threat(region_idx, existing_cells)

    land_cells = numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0]

    # Identify the best place to settle based on a sampling of possible cells
    for _ in range(CityCount):
        culture = cultures[0]

        samples = random.choices(land_cells, k=SampleSize)
        scores = list( map(lambda idx: score(idx, culture), samples) )

        top_cell_idx = samples[scores.index(max(scores))]

        cities.append( City(top_cell_idx) )

    # Add all cities to the world
    for city in cities:
        world.add_entity(city)