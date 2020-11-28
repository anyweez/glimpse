import enum, numpy, random

from entity import Entity
from world import Cell
from decorators import genreq

class PointOfInterest(Entity):
    Type = enum.Enum('POIType', 'LAKE MOUNTAIN')

    def __init__(self, graph, poi_type):
        super().__init__(graph)

        self.type = poi_type

def findLakes(cell_idxs, graph):
    LakeMinSize = 6
    LakeMaxSize = 40

    open_cells = set(cell_idxs)

    while len(open_cells) > 0:
        start_idx = random.choice( list(open_cells) )
        idxs = graph.floodfill(start_idx)

        if len(idxs) >= LakeMinSize and len(idxs) <= LakeMaxSize:
            # Generate a lake POI
            def in_lake(edge):
                return edge[0] in idxs and edge[1] in idxs

            yield PointOfInterest(
                graph.subgraph(in_lake),
                PointOfInterest.Type.LAKE,
            )

        # Discard all of these cells, which have all now been considered
        for idx in idxs:
            open_cells.discard(idx)

        open_cells.discard(start_idx)

def findMountains(cell_idxs, graph):
    MountainMinSize = 6
    MountainMaxSize = 50

    open_cells = set(cell_idxs)

    while len(open_cells) > 0:
        start_idx = random.choice( list(open_cells) )
        idxs = graph.floodfill(start_idx)

        if len(idxs) >= MountainMinSize and len(idxs) <= MountainMaxSize:
            # Generate a mountain POI
            def in_mountain(edge):
                return edge[0] in idxs and edge[1] in idxs

            yield PointOfInterest(
                graph.subgraph(in_mountain),
                PointOfInterest.Type.MOUNTAIN,
            )
        
        # Discard all of these cells, which have all now been considered
        for idx in idxs:
            open_cells.discard(idx)

        open_cells.discard(start_idx)

@genreq(cellprops=['celltype',])
def generate(world, vd):
    '''
    Detect all points of interest in the provided world. This function returns a 'library'
    containing all of the POI's organized by type.
    '''
    def edge_filter_water(edge):
        (src, dest) = edge

        return world.cp_celltype[src] == Cell.Type.WATER and \
            world.cp_celltype[dest] == Cell.Type.WATER

    def edge_filter_mountain(edge):
        (src, dest) = edge

        return world.cp_celltype[src] == Cell.Type.LAND and \
            world.cp_celltype[dest] == Cell.Type.LAND and \
            world.cp_elevation[src] > 0.6 and \
            world.cp_elevation[dest] > 0.6

    watergraph = world.graph.subgraph(edge_filter_water)
    mountaingraph = world.graph.subgraph(edge_filter_mountain)

    # Find all lakes
    for lake in findLakes(numpy.argwhere(world.cp_celltype == Cell.Type.WATER)[:, 0], watergraph):
        world.add_entity(lake)

    for mountain in findMountains(numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0], mountaingraph):
        world.add_entity(mountain)
