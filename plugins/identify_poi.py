import enum, numpy, random, itertools, collections, math, itertools

from shapely.geometry.point import Point
import langserver_conf as lsc

from entity import Entity
from world import Cell
from decorators import genreq

lc = lsc.GetClient()
next_poi_id = 1

class PointOfInterest(object):
    Type = enum.Enum('POIType', 'LAKE MOUNTAIN SEA BAY')
    next_id = itertools.count()
    
    def __init__(self, poi_type):
        self.id = next(self.next_id)

        self.type = poi_type
    
        if self.type == PointOfInterest.Type.LAKE:
            self.fetch_name('english', 'lake', {})
        
        if self.type == PointOfInterest.Type.MOUNTAIN:
            self.fetch_name('english', 'mountain', {})
        
        if self.type == PointOfInterest.Type.SEA:
            self.fetch_name('english', 'sea', {})

        if self.type == PointOfInterest.Type.BAY:
            self.fetch_name('english', 'bay', {})

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

            if entity_type == 'bay':
                if random.random() < 0.2:
                    self.name = 'Bay of {}'.format(self.name)
                else:
                    self.name = '{} Bay'.format(self.name)

            return self.name

BayProspect = collections.namedtuple('BayProspect', ['src', 'dest', 'mouth', 'sinuosity', 'coast'])

BAY_SINUOSITY_MIN = 3.0
BAY_MAX_PER_LANDFORM = 4

@genreq(cellprops=['celltype',], worldparams=['has_lakes'])
def generate(world, vd):
    '''
    Detect all points of interest in the provided world.
    '''
    Unassigned = -1
    waterbody_arr = world.new_cp_array(numpy.int16, Unassigned)


    def land_only(edge):
        return world.cp_celltype[ edge[0] ] == Cell.Type.LAND and \
            world.cp_celltype[ edge[1] ] == Cell.Type.LAND

    def water_only(edge):
        return world.cp_celltype[ edge[0] ] == Cell.Type.WATER and \
            world.cp_celltype[ edge[1] ] == Cell.Type.WATER

    # def coast_cell(edge):
    #     return world.cp_celltype[ edge[0] ] == Cell.Type.LAND and \
    #         world.cp_celltype[ edge[1] ] == Cell.Type.WATER

    landgraph = world.graph.subgraph(land_only)
    watergraph = world.graph.subgraph(water_only)
    # Coast graph contains land cells that border water
    # coastgraph = world.graph.subgraph(coast_cell)

    # Detection based on water cells
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

    # Detection based on land cells
    bays = []
    for landform_id in [id for id in numpy.unique(world.cp_landform_id) if id != -1]:
        # Get all cells with the current landform_id
        cell_idxs = numpy.argwhere(world.cp_landform_id == landform_id)[:, 0]

        coast_cells = set()
        inland_cells = set()

        # print('landform {}, part 1 (total_n={})'.format(landform_id, len(cell_idxs)))

        # Identify whether each cell is inland or on the coast
        for cell_idx in [idx for idx in cell_idxs if waterbody_arr[idx] == Unassigned]:
            neighbors = world.graph.neighbors(cell_idx)

            coastal = any( [idx for idx in neighbors if world.cp_celltype[idx] == Cell.Type.WATER] )

            if coastal:
                coast_cells.add(cell_idx)
            else:
                inland_cells.add(cell_idx)

        def coast_only(edge):
            return edge[0] in coast_cells and edge[1] and coast_cells

        coastgraph = landgraph.subgraph(coast_only)
        coastal_prospects = []

        for src, dest in itertools.product( list(coast_cells), list(coast_cells) ):
            # Prevent cases where src == dest and arbitrary choice to avoid evaluating (src, dest)
            # and (dest, src).
            if src < dest:
                mouth = world.graph.shortest_path(src, dest) # slice off src and dest

                # If all cells on the shortest path are water (no land), consider this possibility.
                # A path length of two means we're looking at two coastal cells directly beside each other.
                if len(mouth) > 2 and all( [world.cp_celltype[idx] == Cell.Type.WATER for idx in mouth[1:-1]] ):
                    coast = coastgraph.shortest_path(src, dest)
                    sinuosity = len(coast) / len(mouth)

                    if sinuosity > BAY_SINUOSITY_MIN and len(coast) > 4:
                        bp = BayProspect(src=src, dest=dest, sinuosity=sinuosity, mouth=mouth, coast=coast)
                        coastal_prospects.append( bp )

        coastal_prospects = sorted(coastal_prospects, key=lambda cp: cp.sinuosity, reverse=True)

        # Label the mouths of these bays. Once a cell is part of a bay, no other bay may
        # overlap. Important that we sort by sinuosity DESC so the most defined bays get
        # precedent.
        labeled_cells = set()

        # TODO: ALTERNATIVE APPROACH
        # Randomly sample X points in the watergraph. Keep expanding each point to X% of the world volume.
        # Iteratively expand the size of each point until it exceeds X% of the size of the world -- if at
        # any point the n vs n+1 volume increases by < Y then lock in as a bay.

        for cp in coastal_prospects[0: min(BAY_MAX_PER_LANDFORM, len(coastal_prospects))]:
            bay = PointOfInterest(PointOfInterest.Type.BAY)
            world.add_entity(bay)
            bays.append(bay)    # track bays so we can merge once all have been discovered

            # Split the watergraph by the mouth of the bay; this should result into two main
            # subgraphs. Check all water neighbors from the smallest subgraph via floodfill.
            # FIXME: work in progress, doesn't work yet
            coast_midpoint_idx = math.floor(len(cp.coast) / 2)
            mouth_midpoint = cp.mouth[ math.floor(len(cp.mouth) / 2) ]

            # Find the water neighbor closest to the mouth of the bay
            potential_water_seeds = set()

            for incr in range(-2, 2):
                coast_idx = coast_midpoint_idx + incr

                local_neighbors = [idx 
                    for idx in world.graph.neighbors(cp.coast[coast_idx]) \
                    if world.cp_celltype[idx] == Cell.Type.WATER \
                ]

                for idx in local_neighbors:
                    potential_water_seeds.add(idx)

            water_seeds = list( map(
                lambda water_idx: (water_idx, watergraph.distance(water_idx, lambda dest_idx: dest_idx == mouth_midpoint)[1]), 
                list(potential_water_seeds),
            ) )

            # Only consider water cells that are connected to the mouth via the watergraph. Find
            # the closest water seed and use that to build up the `body`.
            water_seeds = list( filter(lambda ws: ws[1] is not None, water_seeds) )
            # Get the nearest (first in sorted order), and only keep the cell_idx and discard the
            # distance.
            body = set(cp.mouth[1:-1])

            if len(water_seeds) > 0:
                nearest_water_cell = sorted(water_seeds, key=lambda ws: ws[1])[0][0]

                body.add(nearest_water_cell)
                next_round = [nearest_water_cell,]

                # Continue expanding the bay until either there's nowhere else to expand or
                # we reach 5% of the map.
                while len(next_round) > 0 and len(body) <= world.cell_abs(0.05):
                    next_cell = next_round.pop()
                    
                    for cell_idx in watergraph.neighbors(next_cell):
                        if cell_idx not in body and waterbody_arr[cell_idx] == Unassigned:
                            next_round.append(cell_idx)
                            body.add(cell_idx)

            for cell_idx in list(body):
                waterbody_arr[cell_idx] = bay.id
                labeled_cells.add(cell_idx)

        # Merge bays that touch each other
        for idx, first in enumerate(bays):
            for second in bays[idx + 1:]:
                first_idx = numpy.argwhere(waterbody_arr == first.id)[:, 0]
                second_idx = set( numpy.argwhere(waterbody_arr == second.id)[:, 0] )
                
                # Check if any of the cells in the first bay are neighbors of any
                # cells in the second bay. If so, replace second.id in waterbody_arr
                # with first.id (removing second.id entirely).
                for cell_idx in first_idx:
                    for neighbor in watergraph.neighbors(cell_idx):
                        if neighbor in second_idx:
                            for idx in range(len(waterbody_arr)):
                                if waterbody_arr[idx] == second.id:
                                    waterbody_arr[idx] = first.id
                

    world.add_cell_property('waterbody_id', waterbody_arr)