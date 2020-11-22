import enum
import structs

from structs import Cell

class PointOfInterest(structs.AbstractCellGroup):
    Type = enum.Enum('POIType', 'LAKE MOUNTAIN')

    def __init__(self, cells, vor, graph, poi_type):
        super().__init__(cells, vor, graph)

        self.type = poi_type

class PointOfInterestLibrary(object):
    def __init__(self, poi_dict):
        self.poi_dict = poi_dict

        for poi_type in self.list_types():
            if poi_type not in self.poi_dict:
                self.poi_dict[poi_type] = []

    def get_type(self, poi_type):
        return self.poi_dict[poi_type]

    def list_types(self):
        return list(PointOfInterest.Type)

def _checkForLake(region_idx, world, existing_lakes):
    '''
    Check to see if the specified cell is part of a lake. If so, return a LAKE PointOfInterest.
    If not, return None.
    '''
    LakeMinSize = 3
    LakeMaxSize = 40

    # If this isn't a water cell, can't be a lake
    if world.get_cell(region_idx).type != Cell.Type.WATER:
        return None

    idxs = world.graph.floodfill(region_idx, lambda idx: world.get_cell(idx).type == Cell.Type.WATER)
    
    if len(idxs) >= LakeMinSize and len(idxs) <= LakeMaxSize:
        return PointOfInterest(
            world.get_cells(idxs),
            world.vor,
            world.graph,
            PointOfInterest.Type.LAKE,
        )

    return None

def _checkForMountain(region_idx, world, existing_mountains):
    '''
    Check to see if the specified cell is part of a mountain. If so, return a MOUNTAIN
    PointOfInterest. If not, return None.
    '''
    MountainMinSize = 8
    MountainMaxSize = 30
    MountainMinHeight = 0.6

    # A mountain is land with elevation > MountainMinHeight
    def is_mountain(idx):
        cell = world.get_cell(idx)

        return cell.type == Cell.Type.LAND and cell.elevation > MountainMinHeight

    # If this cell is not a mountain, no need to floodfill.
    if not is_mountain(region_idx):
        return None
    
    idxs = world.graph.floodfill(region_idx, is_mountain)

    if len(idxs) >= MountainMinSize and len(idxs) <= MountainMaxSize:
        return PointOfInterest(
            world.get_cells(idxs),
            world.vor,
            world.graph,
            PointOfInterest.Type.MOUNTAIN,
        )

    return None

def _already_detected(region_idx, existing):
    '''
    Ensure we don't test cells that are already a part of a known POI of a certain type.
    For example, if a cell is already part of a known lake, we don't need to test to see
    whether its part of a lake.
    '''
    return len([item for item in existing if item.contains(region_idx)]) > 0

def DetectAll(world):
    '''
    Detect all points of interest in the provided world. This function returns a 'library'
    containing all of the POI's organized by type.
    '''

    pois = {}
    for poi_type in list( PointOfInterest.Type ):
        pois[poi_type] = []

    poi_categories = [
        { 'func': _checkForLake, 'poi_type': PointOfInterest.Type.LAKE, 'cell_type': Cell.Type.WATER },
        { 'func': _checkForMountain, 'poi_type': PointOfInterest.Type.MOUNTAIN, 'cell_type': Cell.Type.LAND },
    ]

    for category in poi_categories:
        poi_type = category['poi_type']

        cells = [c for c in world.cells if c.type == category['cell_type'] and not _already_detected(c.region_idx, pois[poi_type])]

        for cell in cells:
            next_poi = category['func'](cell.region_idx, world, pois[poi_type])

            if next_poi is not None:
                pois[poi_type].append(next_poi)

    library = PointOfInterestLibrary(pois)

    for poi_type in library.list_types():
        print( '%s => %s' % (poi_type, len(library.get_type(poi_type))) )

    return library