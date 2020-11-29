class Culture(object):
    '''
    Cultures are responsible for the logic related to decisions for intelligent life, i.e. how things are
    named (what language? what rules?) and where cities are placed.

    Cultures can represent different races (orcs, humans, elves), different subgroups (desert-dwelling humans
    vs mountain-dwelling humans), or different alliances.
    '''

    def __init__(self, lang, world):
        self.lang = lang
        self.world = world

    def city_survivability(self, idx, other_idx):
        raise NotImplementedError()

    def city_economy(self, idx, other_idx):
        raise NotImplementedError()

    def city_threat(self, idx, other_idx):
        raise NotImplementedError()