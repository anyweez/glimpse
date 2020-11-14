import matplotlib.pyplot as plt
import enum, random, math, colour, collections, numpy, functools, string, pprint
import errors

from scipy.spatial import voronoi_plot_2d
from PIL import Image
from noise import snoise2

class Cell(object):
    '''
    Cells represent sections of a World that have certain characteristics like terrain types
    and elevation. Cells are spatially defined by polygons, which are currently equivalent 
    to regions of a Voronoi diagram.
    '''
    Type = enum.Enum('CellType', 'NONE WATER LAND FIRE')

    def __init__(self, region_idx, location):
        self.region_idx = region_idx
        self.location = location
        self.neighbor_to = []

        # Does this cell exist on the border of the world?
        self.is_boundary = False

        self.type = Cell.Type.NONE
        self.elevation = 0

        # What tectonic plate is this cell a part of?
        self.plate_id = None

    @staticmethod
    def FormCells(vor):
        '''
        Generate a series of world cells based on the specified Voronoi diagram. A directed
        graph is also calculated based on which cells are touching each other.
        '''
        cells = []

        for point_idx, region_idx in enumerate(vor.point_region):
            cell = Cell(region_idx, vor.points[point_idx])

            cells.append(cell)

        return cells

class AbstractCellGroup(object):
    def __init__(self, cells, vor, graph):
        self.cells = cells
        self.vor = vor
        self.graph = graph

        self.available_cells = {}
        self.vertex_count = {}

        # Populate self.available_cells
        for cell in self.cells:
            self.available_cells[cell.region_idx] = cell

        # Populate self.vertex_count
        for cell in self.cells:
            indeces = set( vor.regions[cell.region_idx] )

            for idx in indeces:
                if idx not in self.vertex_count:
                    self.vertex_count[idx] = 0
                
                self.vertex_count[idx] += 1

    def contains(self, region_idx):
        return region_idx in self.available_cells

    def get_region(self, region_idx):
        '''
        Get the polygon that defines the region for the specified cell_id/region_id.
        Returns a list of 2D points, or an empty list if the region isn't defined within
        the Voronoi diagram; see more about when this happens here:

        https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Voronoi.html
        '''
        if -1 in self.vor.regions[region_idx]:
            return []

        return list( map(lambda r: self.vor.vertices[r], self.vor.regions[region_idx]) )

    def get_vertices(self, region_idx):
        if -1 in self.vor.regions[region_idx]:
            return []

        return self.vor.regions[region_idx]

    def get_cell(self, region_idx):
        if isinstance(region_idx, Cell):
            raise Exception('Provide a region_idx, not a Cell')

        if region_idx not in self.available_cells:
            raise errors.InvalidCellError('Requested non-existant or out of scope cell #%d' % (region_idx,))

        return self.available_cells[region_idx]

    def get_cells(self, region_idxs):
        # NOTE TO FUTURE SELF: I'm intentionally deciding that this function should only
        # return the cells that exist in scope. I'm running into an issue where the graph
        # is aware of all worldwide cells but worldregions only have access to certain cells.
        #
        # I expect this is going to be a fairly common case, and regions should never operate
        # on cells outside of their scope so I think its safe to make this decision. I have
        # a troubling feeling that not providing any notification is going to generate nasty
        # bugs, though.
        return [self.available_cells[idx] for idx in region_idxs if idx in self.available_cells]



class WorldRegion(AbstractCellGroup):
    def __init__(self, cells, vor, graph):  
        super().__init__(cells, vor, graph)

    def watershed(self):
        '''
        Create lakes in low 'bowls' where water runs downhill and doesn't have a way to get out to an
        ocean. Simulate rainfall and fill areas at the bottom of the hill.
        '''

        water_depth = {}

        for cell in self.cells:
            water_depth[cell.region_idx] = 0

        # Find the cell with the lowest elevation out of a list of cells
        def lowest_cell(all_cells):
            return functools.reduce(lambda a, b: a if a.elevation < b.elevation else b, all_cells, all_cells[0])

        # For each land cell, visit neighbors @ lower elevations until you reach water or don't have
        # neighbors @ lower elevation. If you reach water, end with no side-effects. If you reach a
        # bowl, increase water depth by one.
        for current_cell in [c for c in self.cells if c.type == Cell.Type.LAND]:
            neighbors = self.get_cells( self.graph.neighbors(current_cell.region_idx) )
            next_cell = lowest_cell(neighbors)

            # Keep flowing while 
            while next_cell.elevation < current_cell.elevation:
                current_cell = next_cell

                neighbors = self.get_cells( self.graph.neighbors(current_cell.region_idx) )
                next_cell = lowest_cell(neighbors)

                # If we've hit a cell that's already water, finish.
                if next_cell.type == Cell.Type.WATER:
                    break
            
            # If we ended on land, increase water depth.
            if next_cell.type == Cell.Type.LAND:
                water_depth[next_cell.region_idx] += 1

        # Convert cells to water if enough water has pooled up. If the pool is big enough, start
        # filling up surrounding cells as well.
        for (region_idx, depth) in water_depth.items():
            if depth > 5:
                cell = self.get_cell(region_idx)
                cell.type = Cell.Type.WATER

                pool = [cell,]

                # If we've over-filled a cell, flow into the next lowest cell connected to the pool.
                # Each time the pool expands, future expansions can go into the neighboring LAND cells
                # connected to any part of the pool. The lowest elevation cell will always be selected.
                for _ in range( math.floor(depth / 10) ):
                    neighbors = []
                    for c in pool:
                        for neighbor in [n for n in self.get_cells( self.graph.neighbors(c.region_idx) ) if n.type == Cell.Type.LAND]:
                            neighbors.append(neighbor)
    
                    # Its rare but possible that a cell won't have any LAND neighbors, which causes a crash without this check.
                    if len(neighbors) > 0:
                        lowest = lowest_cell(neighbors)

                        lowest.type = Cell.Type.WATER
                        pool.append(lowest)

    '''
    Check whether the specified region is on the 'border' of the region. A cell is on the border if
    it contains a vertex that isn't shared by any other cell in the region.
    '''
    def is_border(self, region_idx):
        if region_idx not in self.available_cells:
            raise errors.InvalidCellError('Cell does not exist in region')

        for r in self.get_vertices(region_idx):
            if self.vertex_count[r] == 1:
                return True
        
        return False

class Landform(AbstractCellGroup):
    def __init__(self, cells, vor, graph):
        super().__init__(cells, vor, graph)

    # TODO: move to AbstractCellGroup?
    def contains(self, region_idx):
        try:
            return self.get_cell(region_idx)
        except errors.InvalidCellError:
            return False

    def outline(self):
        ridges = []

        '''
        get all allowed regions
        for all ridge vertices
            check if ridge is in exactly one region
        '''
        supported_regions = list( map(lambda cell: self.vor.regions[cell.region_idx], self.cells) )

        regions_with_ridge = lambda ridge: list( filter(lambda region: ridge[0] in region and ridge[1] in region, supported_regions) )

        for ridge in self.vor.ridge_vertices:
            if len(regions_with_ridge(ridge)) == 1 and -1 not in ridge:
                ridges.append(ridge)

        return list(map(lambda r: (self.vor.vertices[r[0]], self.vor.vertices[r[1]]), ridges))


class World(AbstractCellGroup):
    '''
    Worlds contain a series of Cells, and store the Voronoi diagram used to define the region
    and position of each. Worlds also include much of the logic for world generation and any 
    configuration variables needed to do so.
    '''

    # Currently worldwide configuration so elevation looks smooth across nearby landforms and (eventually)
    # underwater surfaces.

    # Definition of what these are here:
    # http://libnoise.sourceforge.net/glossary/
    NoiseConfig = {
        'scale': 2.5,           # top tweak
        'octaves': 5,
        'persistence': 4.5,
        'lacunarity': 2.0,
        'base': random.randint(0, 1000)
    }

    LandformConfig = {
        'InitialPlateSplitProb': 0.01,
        'InitialContinentMin': 1,
        'InitialContinentMax': 12,
    }

    def __init__(self, cells, vor, graph):
        super().__init__(cells, vor, graph)

        self.continents = []
        self.id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def CreateRegion(self, cells):
        if self.graph is None:
            raise Exception('You must build() the world before you can create regions in it.')

        return WorldRegion(cells, self.vor, self.graph)

    def _gen_noise(self, x, y):
        scaled_x = x / World.NoiseConfig['scale']
        scaled_y = y / World.NoiseConfig['scale']

        octaves = World.NoiseConfig['octaves']
        persistence = World.NoiseConfig['persistence']
        lacunarity = World.NoiseConfig['lacunarity']

        base = World.NoiseConfig['base']

        return ( snoise2(scaled_x, scaled_y, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=base) + 1.0) / 2.0

    def build(self):
        self._label_boundary(self.cells)

        # Establish tectonic plates. Once this is done we'll create a separate region for each.
        wr = self.CreateRegion(self.cells)
        self._form_plates(wr)

        gen_noise = lambda x, y: self._gen_noise(x, y)

        # Run world generation functions on each plate independently.
        for plate_id in set( [c.plate_id for c in self.cells] ):
            cells = [c for c in self.cells if c.plate_id == plate_id]

            region = self.CreateRegion(cells)

            self._add_ocean(region)
            self._terrainify(region)
            self._add_elevation(region, gen_noise)
            
            region.watershed()
        
    def label(self):
        wr = self.CreateRegion(self.cells)

        # Start a continuent at a random land cell
        land_cells = list( filter(lambda c: c.type == Cell.Type.LAND, self.cells) )

        for cell in land_cells:
            # if the cell is not yet part of a continent
            if len( list(filter(lambda con: con.contains(cell.region_idx), self.continents)) ) == 0:
                # Flood fill across Land cells to generate the full continent
                cell_idxs = wr.graph.floodfill(cell.region_idx, lambda c: self.get_cell(c).type == Cell.Type.LAND)

                # Create a Landform and add it to the continent list
                self.continents.append( Landform(self.get_cells(cell_idxs), self.vor, self.graph) )

    def _form_plates(self, region):
        num_plates = random.randint(
            World.LandformConfig['InitialContinentMin'], 
            World.LandformConfig['InitialContinentMax'], 
        )

        plate_centers = random.choices(region.cells, k=num_plates)
        plate_dist = [1,] * num_plates  # distance to go out from the center to find available cells

        for idx, center in enumerate(plate_centers):
            center.plate_id = idx

        # Function to check whether a cell still needs to have a plate assigned. Boundary cells
        # are excluded.
        still_available = lambda idx: self.get_cell(idx).plate_id is None

        remaining = sum( [1 for cell in region.cells if still_available(cell.region_idx)] )

        # Add all cells to a plate
        while remaining > 0:
            # For each plate, expand out from the center
            for plate_id, center in enumerate(plate_centers):
                avail = [idx for idx in region.graph.neighbors(center.region_idx, plate_dist[plate_id]) if still_available(idx)]

                while len(avail) == 0:
                    plate_dist[plate_id] += 1
                    avail = [idx for idx in region.graph.neighbors(center.region_idx, plate_dist[plate_id]) if still_available(idx)]

                mark = self.get_cell( random.choice(avail) )
                mark.plate_id = center.plate_id

                # Count remaining cells to be marked; break the loop if we're done.
                remaining = sum( [1 for cell in region.cells if still_available(cell.region_idx)] )

                if remaining == 0:
                    break

            # There's a chance to add a new plate each iteration. New plates
            # can only exist in unmarked cells.
            if random.random() < (World.LandformConfig['InitialPlateSplitProb'] / len(plate_centers)):
                avail = [c for c in self.cells if c.plate_id is None]

                if len(avail) > 0:
                    cell = random.choice(avail)
                    
                    cell.plate_id = len(plate_centers)
                    plate_centers.append(cell)
                    plate_dist.append(1) # all plates start at dist=1

    '''
    A boundary cell is a cell that extends beyond the edge of the world.
    '''
    def _label_boundary(self, cells):
        for cell in cells:
            region = self.get_region(cell.region_idx)

            if region == []:
                cell.is_boundary = True
            else:
                for (x, y) in region:
                    if x > 1.0 or x < 0.0:
                        cell.is_boundary = True
                    if y > 1.0 or y < 0.0:
                        cell.is_boundary = True

    '''
    All cells at the edge of the map are water. We then traverse the graph from each of the boundary cells
    and mark cells along the path as water (% chance).
    '''
    def _add_ocean(self, region):
        for cell in region.cells:
            if region.is_border(cell.region_idx):
                cell.type = Cell.Type.WATER

                # Traverse the cell graph twice randomly and turn each cell into
                # water. Two anecdotally gives decent results when PointCount = 250,
                # but the number should probably be a function of the number of cells.
                neighbor = cell

                iterations = round( math.sqrt(math.sqrt(len(region.cells))) )

                for _ in range(iterations):
                    if (random.random() < 0.8):
                        avail = region.graph.neighbors(neighbor.region_idx)

                        if len(avail) > 0:
                            neighbor = self.get_cell( random.choice(avail) )
                            neighbor.type = Cell.Type.WATER

    def _terrainify(self, region):
        for cell in region.cells:
            if not cell.type == Cell.Type.WATER:
                cell.type = Cell.Type.LAND

    def _add_elevation(self, region, gen_noise):
        # Different regions may have different elevation profiles - some will be more
        # mountainous and others may be flatter. The 'dampener' approximates this profile
        # and is assigned randomly. Regions with smaller dampener values will tend to be
        # flatter.
        #
        # TODO: improve this -- really cool effect but did this in 30 seconds
        dampener = random.choice([0.4, 0.4, 0.6, 1.0])

        for cell in region.cells:
            if cell.type == Cell.Type.LAND:
                cell.elevation = gen_noise(cell.location[0], cell.location[1]) * dampener

                # (_, dist_from_water) = self.graph.distance(
                #     cell.region_idx, 
                #     lambda _, idxs, __: idxs, 
                #     lambda idx: region.get_cell(idx).type == Cell.Type.WATER
                # )
                dist_from_water = self.__distance_from_water(cell, region)

                if dist_from_water < 5:
                    fade_pct = [.3, .5, .8, .9]
                    cell.elevation = cell.elevation * fade_pct[dist_from_water - 1]

    '''
    Find the shortest distance from the specified cell to water. Distance is defined
    as the lowest number of edges in the world graph that need to be traversed to 
    reach a water cell.

    TODO: transition to using graph.distance()
    '''
    def __distance_from_water(self, cell, region):
        queue = collections.deque()
        queue.append( (cell.region_idx, 0) )

        # Keep track of which cells have already been searched.
        added = set()
        added.add(cell.region_idx)

        while len(queue) > 0:
            (idx, dist) = queue.popleft()
            cell = self.get_cell(idx)

            if cell.type == Cell.Type.WATER:
                return dist

            for next_idx in region.graph.neighbors(idx):
                if next_idx not in added:
                    queue.append( (next_idx, dist + 1) ) 
                    added.add( next_idx )

    # def render(self, cities=[], cell_labels=False, color_boundaries=False, cell_elevation=False, tectonics=False, show_graph=False, outline_landforms=False, heightmap=False):
    #     def paint_cell(cell_id, color):
    #         '''
    #         Fill the specified cell's region with the specified `color`. Supported colors are documented here:
    #             https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.fill.html
    #         '''
    #         region = self.get_region(cell_id)

    #         x = list( map(lambda p: p[0], region) )
    #         y = list( map(lambda p: p[1], region) )
    #         plt.fill(x, y, color)

    #     voronoi_plot_2d(self.vor, show_vertices=False, show_points=False, line_width=0)
    #     axes = plt.gca()

    #     axes.set_xlim([0, 1])
    #     axes.set_ylim([0, 1])

    #     if cell_labels:
    #         for cell in self.cells:
    #             plt.text(cell.location[0], cell.location[1], cell.region_idx, fontsize=8)

    #     if color_boundaries:
    #         for cell in self.cells:
    #             if cell.type == Cell.Type.WATER:
    #                 paint_cell(cell.region_idx, '#0485d1')
    #             if cell.type == Cell.Type.LAND:
    #                 paint_cell(cell.region_idx, 'g')
    #             if cell.type == Cell.Type.FIRE:
    #                 paint_cell(cell.region_idx, 'red')

    #     if cell_elevation:
    #         color_sealevel = colour.Color('green')
    #         color_peak = colour.Color('red')

    #         num_colors = 25
    #         gradient = list( color_sealevel.range_to(color_peak, num_colors) )

    #         for cell in self.cells:
    #             if cell.type == Cell.Type.LAND:
    #                 color_idx = math.floor( cell.elevation / (1.0 / num_colors) )
    #                 paint_cell(cell.region_idx, gradient[color_idx].hex)

    #     if tectonics:
    #         num_plates = len( set([c.plate_id for c in self.cells]) )

    #         print('num_plates=%d' % (num_plates))
    #         random_color = lambda: colour.rgb2hex( (random.random(), random.random(), random.random()) )
    #         colors = [ random_color() for plate in range(num_plates) ]
            
    #         for cell in self.cells:
    #             # self.paint_cell(cell.region_idx, colors[cell.plate_id])

    #             plt.text(cell.location[0], cell.location[1], cell.plate_id, fontsize=8)

    #     if show_graph:
    #         for node in self.cells[0:100]:
    #             for neighbor in node.neighbor_to:
    #                 x = (node.location[0], neighbor.location[0])
    #                 y = (node.location[1], neighbor.location[1])

    #                 plt.plot(x, y, linestyle='dashed', color='red', linewidth=1)

    #             plt.plot(node.location[0], node.location[1], 'bo')

    #     if outline_landforms:
    #         for continent in self.continents:
    #             outlines = continent.outline()

    #             for outline in outlines:
    #                 x = (outline[0][0], outline[1][0])
    #                 y = (outline[0][1], outline[1][1])

    #                 plt.plot(x, y, '#222222', linewidth=1)

    #     if heightmap:
    #         grid = numpy.zeros((1000, 1000),)

    #         for y in range(1000):
    #             for x in range(1000):
    #                 grid[x][y] = self._gen_noise(x / 1000.0, y / 1000.0)

    #         grid = (255 * grid).astype('uint8')
    #         img = Image.fromarray(grid, mode='L')
    #         img.save('heightmap.png')

    #     if len(cities) > 0:
    #         for city in cities:
    #             plt.plot(city.location[0], city.location[1], marker='o', markersize=3, color='red')

    #     plt.title('Rendered world')

    #     plt.savefig('world.png')
    #     # plt.savefig('world-%s.png' % (self.id,))
    #     # plt.show()
