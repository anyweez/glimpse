import enum, numpy, random, itertools

from shapely.geometry.point import Point
import langserver_conf as lsc

from entity import Entity
from world import Cell
from decorators import genreq

lc = lsc.GetClient()
next_poi_id = 1

class PointOfInterest(object):
    Type = enum.Enum('POIType', 'LAKE MOUNTAIN SEA')
    next_id = itertools.count()
    
    # def __init__(self, cell_idx, graph, poi_type):
    def __init__(self, poi_type):
        # super().__init__(graph)
        self.id = next(self.next_id)

        self.type = poi_type
        # self.cell_idx = cell_idx
        # self.graph = graph

        if self.type == PointOfInterest.Type.LAKE:
            self.fetch_name('english', 'lake', {})
        
        if self.type == PointOfInterest.Type.MOUNTAIN:
            self.fetch_name('english', 'mountain', {})
        
        if self.type == PointOfInterest.Type.SEA:
            self.fetch_name('english', 'sea', {})

    def contains(self, cell_idx):
        return self.graph.contains_cell(cell_idx)

    def fetch_name(self, language, entity_type, params):
        if hasattr(self, 'name'):
            return self.name
        else:
            self.name = lc.get_name(language, entity_type, params)

            # TODO: move to language server
            if entity_type == 'sea':
                self.name = '{} Sea'.format(self.name)

            return self.name

def center(cell_idxs, world):
    cell_x = []
    cell_y = []

    for idx in cell_idxs:
        cell_x.append(world.cp_longitude[idx])
        cell_y.append(world.cp_latitude[idx])

    x = sum(cell_x) / len(cell_x)
    y = sum(cell_y) / len(cell_y)

    return (x, y)

def findLakes(cell_idxs, graph, world, vd):
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

            center_pt = center(idxs, world)
            center_idx = vd.find_cell(center_pt[0], center_pt[1])

            yield PointOfInterest(
                center_idx,
                graph.subgraph(in_lake),
                PointOfInterest.Type.LAKE,
            )

        # Discard all of these cells, which have all now been considered
        for idx in idxs:
            open_cells.discard(idx)

        open_cells.discard(start_idx)

def findMountains(cell_idxs, graph, world, vd):
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

            center_pt = center(idxs, world)
            center_idx = vd.find_cell(center_pt[0], center_pt[1])

            yield PointOfInterest(
                center_idx,
                graph.subgraph(in_mountain),
                PointOfInterest.Type.MOUNTAIN,
            )
        
        # Discard all of these cells, which have all now been considered
        for idx in idxs:
            open_cells.discard(idx)

        open_cells.discard(start_idx)

@genreq(cellprops=['celltype',], worldparams=['has_lakes'])
def generate(world, vd):
    '''
    Detect all points of interest in the provided world.
    '''
    Unassigned = -1
    waterbody_arr = world.new_cp_array(numpy.int16, Unassigned)

    def water_only(edge):
        return world.cp_celltype[ edge[0] ] == Cell.Type.WATER and \
            world.cp_celltype[ edge[1] ] == Cell.Type.WATER

    def coast_cell(edge):
        return world.cp_celltype[ edge[0] ] == Cell.Type.LAND and \
            world.cp_celltype[ edge[1] ] == Cell.Type.WATER

    watergraph = world.graph.subgraph(water_only)
    # Coast graph contains land cells that border water
    coastgraph = world.graph.subgraph(coast_cell)

    for idx in [i for i in world.cell_idxs() if world.cp_celltype[i] == Cell.Type.WATER]:
        if waterbody_arr[idx] == Unassigned:
            waterbody = watergraph.floodfill(idx)

            # Found a lake 
            if world.cell_pct( len(waterbody) ) < 0.1:
                lake = PointOfInterest(PointOfInterest.Type.LAKE)
                world.add_entity(lake)

                for cell_idx in waterbody:
                    waterbody_arr[cell_idx] = lake.id

            # Fully enclosed seas are basically big lakes
            elif world.cell_pct( len(waterbody) ) < 0.25:
                sea = PointOfInterest(PointOfInterest.Type.SEA)
                world.add_entity(sea)

                for cell_idx in waterbody:
                    waterbody_arr[cell_idx] = sea.id
            # TODO: next water body type (ocean, bay, channel, etc)

    world.add_cell_property('waterbody_id', waterbody_arr)

            # next_landform_id += 1

    # def edge_filter_water(edge):
    #     (src, dest) = edge

    #     return world.cp_celltype[src] == Cell.Type.WATER and \
    #         world.cp_celltype[dest] == Cell.Type.WATER

    # def edge_filter_mountain(edge):
    #     (src, dest) = edge

    #     return world.cp_celltype[src] == Cell.Type.LAND and \
    #         world.cp_celltype[dest] == Cell.Type.LAND and \
    #         world.cp_elevation[src] >= world.get_param('MountainMinHeight') and \
    #         world.cp_elevation[dest] >= world.get_param('MountainMinHeight')

    # watergraph = world.graph.subgraph(edge_filter_water)
    # mountaingraph = world.graph.subgraph(edge_filter_mountain)

    # # Find all lakes
    # for lake in findLakes(numpy.argwhere(world.cp_celltype == Cell.Type.WATER)[:, 0], watergraph, world, vd):
    #     world.add_entity(lake)

    # for mountain in findMountains(numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0], mountaingraph, world, vd):
    #     world.add_entity(mountain)
