import random, numpy, math

from entity import Entity
from world import Cell
from decorators import genreq
from cultures.human import HumanCulture

class City(Entity):
    def __init__(self, cell_idx, culture, world):
        super().__init__(None)
        self.cell_idx = cell_idx
        self.culture = culture

        # Determine whether the city is near water for naming purposes; certain names are for
        # seafaring cities only!
        (_, distance) = world.graph.distance(cell_idx, lambda idx: world.cp_celltype[idx] == Cell.Type.WATER, 3)

        self.fetch_name(culture.lang, 'city', {
            'near_water': distance < 3,
        })

    def render_stage2(self, ctx, world, vd, theme):
        city_radius = theme.CityRadius

        city_loc = Entity._transform_pt((
            world.cp_longitude[self.cell_idx],
            world.cp_latitude[self.cell_idx],
        ))

        ctx.set_source_rgba(*theme.CityFill)
        ctx.arc(city_loc[0], city_loc[1], city_radius, 0, 2 * math.pi)
        ctx.fill_preserve()

        ctx.set_source_rgba(*theme.CityBorder)
        ctx.set_line_width(theme.CityBorderWidth)

        ctx.stroke()

@genreq(cellprops=['elevation', 'celltype', 'biome'])
def generate(world, vd):
    SampleSize = 6

    cultures = [
        ( HumanCulture('english', world), 40 ),
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

    def cities_for_culture(cities, culture):
        return len( list( filter(lambda c: c.culture == culture, cities) ) )

    land_cells = numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0]

    active_cultures = [True for _ in cultures]

    # Keep settling while there are high-scoring places to settle. Round robin between cultures.
    while sum(active_cultures) > 0:
        for culture_idx, (culture, min_score) in enumerate(cultures):
            if active_cultures[culture_idx]:
                samples = random.choices(land_cells, k=SampleSize)
                scores = list( map(lambda idx: score(idx, culture), samples) )

                # If at least one cell is above the threshold, settle. If not, this
                # culture is done settling. First settlement gets a pass.
                if cities_for_culture(cities, culture) == 0 or max(scores) > min_score:
                    top_cell_idx = samples[scores.index(max(scores))]

                    # Add city to the world
                    city = City(top_cell_idx, culture, world)

                    cities.append(city)
                    world.add_entity(city)
                else:
                    active_cultures[culture_idx] = False