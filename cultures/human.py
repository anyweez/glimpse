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
        # Cities can't surive in water cells
        if self.world.cp_celltype[idx] == Cell.Type.WATER:
            return -1000.0

        # Provided in same order as biome list in mark_biome.py
        by_biome = (-50.0, -20.0, 3.0, 25.0, 25.0, -20.0, -20.0, 10.0)

        return by_biome[self.world.cp_biome[idx]]

    def city_economy(self, idx, others_idx):
        # Destination is a water cell
        def water(dest_idx):
            return self.world.cp_celltype[dest_idx] == Cell.Type.WATER

        (_, dist) = self.world.graph.distance(idx, water, max_distance=5)

        return (5 - dist) * 10.0 if dist > 0 else 0

    def city_threat(self, idx, others_idx):
        def other_city(dest_idx):
            return dest_idx in others_idx

        # Find the distance to the nearest city. The closer, the more dangerous. Only land cells matter.
        (_, dist) = self.landgraph.distance(idx, other_city, max_distance=20)

        if dist >= 0 and dist < 20:
            return 100.0 - (dist * 5.0)
        else:
            return 0.0