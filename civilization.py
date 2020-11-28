import random
import graph

from world import Cell

class City(object):
    def __init__(self, cell):
        self.cell = cell
        self.location = cell.location

def Score(region_idx, world, culture, existing_cities=[]):
    '''
    Calculate the score of an individual cell for the specified culture. Higher scores
    are more desirable.
    '''
    existing_cells = set( map(lambda city: city.cell.region_idx, existing_cities) )

    c = world.get_cell(region_idx)

    return culture.city_survivability(c.region_idx, world, existing_cells) + \
        culture.city_economy(c.region_idx, world, existing_cells) - \
        culture.city_threat(c.region_idx, world, existing_cells)

def PlaceCity(world, culture, existing_cities):
    top_cell = None
    top_score = -1000000

    for c in random.choices(world.cells, k=25):  
        score = Score(c.region_idx, world, culture, existing_cities)
    
        if score > top_score:
            top_cell = c
            top_score = score

    return City(top_cell)