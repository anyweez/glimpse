import random, numpy, math

from scipy.spatial.kdtree import distance_matrix

from entity import Entity
from world import Cell
from decorators import genreq
from cultures.human import HumanCulture

class City(Entity):
    MaxSize = 5

    def __init__(self, cell_idx, culture, world):
        super().__init__(None)
        self.cell_idx = cell_idx
        self.culture = culture

        # Number of residents; used to calculate size of city
        self.population = 0

        # Determine whether the city is near water for naming purposes; certain names are for
        # seafaring cities only!
        (_, distance) = world.graph.distance(cell_idx, lambda idx: world.cp_celltype[idx] == Cell.Type.WATER, 3)

        self.fetch_name(culture.lang, 'city', {
            'near_water': distance < 3,
        })

    def size(self):
        '''
        The size of the city is based on its population; cities with larger sizes have a higher population.
        '''
        if self.population < 500:
            return 0
        
        if self.population < 1000:
            return 1

        if self.population < 2500:
            return 2
        
        if self.population < 5000:
            return 3
        
        if self.population < 7000:
            return 4
        
        return 5

    def render_stage2(self, ctx, world, vd, theme):
        size_discount = (City.MaxSize - self.size()) * 0.1
        city_radius = theme.CityRadius - ( theme.CityRadius * size_discount )
        border_width = theme.CityBorderWidth - ( theme.CityBorderWidth * size_discount )

        city_loc = Entity._transform_pt((
            world.cp_longitude[self.cell_idx],
            world.cp_latitude[self.cell_idx],
        ))

        ctx.set_source_rgba(*theme.CityFill)
        ctx.arc(city_loc[0], city_loc[1], city_radius, 0, 2 * math.pi)
        ctx.fill_preserve()

        ctx.set_source_rgba(*theme.CityBorder)
        ctx.set_line_width(border_width)

        ctx.stroke()

@genreq(cellprops=['elevation', 'celltype', 'biome'])
def generate(world, vd):
    SampleSize = 6
    GrowthIterations = 10

    cultures = [
        ( HumanCulture('english', world), 20 ),
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
    
    # Simulate growth of cities
    city_region = {}
    for city in cities:
        city_region[city.cell_idx] = world.graph.all_within(city.cell_idx, 10)

        city.population = random.randint(10, 100)

    for _ in range(GrowthIterations):
        for city in cities:
            culture = city.culture
            # Randomly choose 10 nearby cells to measure the benefits of the terrain to the colonizing culture.
            nearby_idxs = random.choices(city_region[city.cell_idx], k=10)

            # Calculate the average carrying capacity of the sampled cells
            carry_cap = sum( map(lambda idx: culture.carrying_capacity(idx), nearby_idxs) ) / len(nearby_idxs)

            # Natural growth
            city.population = culture.pop_change(city.population, carry_cap)

            # Migration
            # depends on distance (% of map) and diff desirability (0-1)
            for dest in cities:
                d_desirability = max(culture.desirability(dest) - culture.desirability(city), 0.0)

                (_, dist) = world.graph.distance(city.cell_idx, lambda idx: idx == dest.cell_idx)
                distance = dist / 100  # normalize based on map size (pct of map)

                pct_migrate = d_desirability * distance

                dest.population = dest.population + (city.population * pct_migrate)
                city.population = city.population - (city.population * pct_migrate)

            if city.population < 0:
                city.population = 0
    
