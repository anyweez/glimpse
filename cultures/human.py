from cultures import culture
from world import Cell

# TODO: not sure 'human' is the right name since diff humans may organize differently -- re-evaluate?
class HumanCulture(culture.Culture):
    def __init__(self, lang, world):
        super().__init__(lang, world)

        def edge_filter(edge):
            (src, dest) = edge

            return self.world.cp_celltype[src] == Cell.Type.LAND and \
                self.world.cp_celltype[dest] == Cell.Type.LAND

        self.landgraph = world.graph.subgraph(edge_filter)
    
    def city_survivability(self, idx, others_idx):
        '''
        Humans can only live on land. They *can* survive in almost any biome, though
        they tend to avoid extremes (tundra, deserts) unless forced there.
        '''
        # Cities can't surive in water cells
        if self.world.cp_celltype[idx] == Cell.Type.WATER:
            return -1000.0

        # Provided in same order as biome list in mark_biome.py
        by_biome = (-50.0, -20.0, 3.0, 25.0, 25.0, -20.0, -20.0, 10.0)

        return by_biome[self.world.cp_biome[idx]]

    def city_economy(self, idx, others_idx):
        '''
        Humans tend to trade on land, but have modest abilities to trade with others
        over water as well if convenient. They're willing to traverse significant distances
        on land to trade.
        '''
        # Destination is a water cell
        def other_city(dest_idx):
            return dest_idx in others_idx

        (_, dist_to_water_p) = self.world.graph.distance(idx, other_city, max_distance=25)
        (_, dist_to_land_p) = self.landgraph.distance(idx, other_city, max_distance=50)

        return max(100.0 - (2 * dist_to_land_p), 100.0 - (4 * dist_to_water_p), 0.0)

    def city_threat(self, idx, others_idx):
        '''
        Humans don't like settling near other cities.
        '''
        def other_city(dest_idx):
            return dest_idx in others_idx

        # Find the distance to the nearest city. The closer, the more dangerous. Only land cells matter.
        (_, dist) = self.landgraph.distance(idx, other_city, max_distance=20)

        return max(120.0 - (dist * 6.0), 0.0)