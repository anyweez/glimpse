import random
import structs, civilization

from poi import PointOfInterest

class Culture(structs.AbstractCellGroup):
    '''
    Cultures are responsible for the logic related to decisions for intelligent life, i.e. how things are
    named (what language? what rules?) and where cities are placed.

    Cultures can represent different races (orcs, humans, elves), different subgroups (desert-dwelling humans
    vs mountain-dwelling humans), or different alliances.
    '''

    def __init__(self, cells, vor, graph, lang):
        super().__init__(cells, vor, graph)

        self.lang = lang
    
    def _name_city(self, city):
        if random.random() < 0.2:
            return 'Fort %s' % (self.lang.generate_name(),)
        
        if random.random() < 0.25:
            return '%s Harbor' % (self.lang.generate_name(),)
        
        if random.random() < 0.35:
            return 'New %s' % (self.lang.generate_name(),)
        
        return self.lang.generate_name()

    def _name_poi(self, poi):
        if poi.type == PointOfInterest.Type.MOUNTAIN and random.random() < 0.50:
            return 'Mount %s' % (self.lang.generate_name(),)

        if poi.type == PointOfInterest.Type.LAKE:
            return 'Lake %s' % (self.lang.generate_name(),)

        return self.lang.generate_name()

    def name_place(self, place):
        '''
        Generate a name for a place based on the Culture's language.
        '''
        if isinstance(place, civilization.City):
            return self._name_city(place)

        if isinstance(place, PointOfInterest):
            return self._name_poi(place)

        return self.lang.generate_name()
    
    def city_survivability(self, idx, world):
        raise NotImplementedError()

    def city_economy(self, idx, world):
        raise NotImplementedError()

    def city_threat(self, idx, world):
        raise NotImplementedError()